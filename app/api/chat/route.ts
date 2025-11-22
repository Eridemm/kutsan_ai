import { GoogleGenerativeAI } from "@google/generative-ai"
import { type NextRequest, NextResponse } from "next/server"

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "")

const PROVIDERS = {
  mistral: {
    name: "Mistral Small 24B",
    endpoint: "https://openrouter.ai/api/v1/chat/completions",
    apiKey: process.env.OPENROUTER_API_KEY,
    model: "mistralai/mistral-small",
    dailyLimit: 10000,
  },
  gemini: {
    name: "Gemini 2.0 Flash",
    dailyLimit: Number.POSITIVE_INFINITY,
  },
}

let dailyUsage = {
  mistral: 0,
  gemini: 0,
  lastReset: new Date().toDateString(),
}

function resetDailyUsageIfNeeded() {
  const today = new Date().toDateString()
  if (dailyUsage.lastReset !== today) {
    dailyUsage = { mistral: 0, gemini: 0, lastReset: today }
  }
}

function selectProvider(): "mistral" | "gemini" {
  resetDailyUsageIfNeeded()

  if (dailyUsage.mistral < PROVIDERS.mistral.dailyLimit) {
    return "mistral"
  }

  return "gemini"
}

async function callMistral(message: string, chatHistory: any[], context?: string): Promise<string> {
  const systemMessage = context
    ? `Sen Türkçe konuşan, öğrenci ve öğretmenlere yardımcı olan bir AI asistansın. 

YÜKLENEN BELGE İÇERİĞİ:
${context}

YETENEKLERİN:
- PDF yükleyerek seni yeni bilgilerle eğitebilirler (fine-tuning)
- Yüklenen belgelerdeki bilgileri öğrenir ve kullanırsın
- Ders kitapları, notlar yüklenince o bilgilere göre cevap verirsin
- SADECE belgede olan bilgileri kullan, bilmiyorsan söyle

KURALLAR:
- Türkçe cevap ver
- Belgeden alıntı yaparken net ol
- Bilgi belgede yoksa "Bu bilgi yüklediğiniz belgede yok" de`
    : `Sen Türkçe konuşan, öğrenci ve öğretmenlere yardımcı olan bir AI asistansın.

YETENEKLERİN:
- PDF yükleyerek seni yeni bilgilerle eğitebilirler
- Ders kitapları, notlar, dökümanlar yüklenir ve sen o bilgileri öğrenirsin
- Her yeni PDF ile daha fazla bilgi edinirsin

ŞU AN: ${context ? "Bir belge yüklü ve o bilgileri kullanıyorum" : "Henüz belge yüklenmedi, genel bilgilerimi kullanıyorum"}

Sorulara net, doğru ve Türkçe cevap ver.`

  const messages = [
    { role: "system", content: systemMessage },
    ...chatHistory.slice(-10).map((m: any) => ({
      role: m.role,
      content: m.content,
    })),
    { role: "user", content: message },
  ]

  const response = await fetch(PROVIDERS.mistral.endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${PROVIDERS.mistral.apiKey}`,
      "HTTP-Referer": process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
      "X-Title": "AI Chatbot",
    },
    body: JSON.stringify({
      model: PROVIDERS.mistral.model,
      messages,
      temperature: 0.7,
      max_tokens: 512,
    }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Mistral API error: ${error}`)
  }

  const data = await response.json()
  return data.choices[0]?.message?.content || "Yanıt alınamadı."
}

async function callGemini(message: string, chatHistory: any[], context?: string): Promise<string> {
  const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-exp" })

  let prompt = `Sen Türkçe konuşan, öğrenci ve öğretmenlere yardımcı olan bir AI asistansın.

YETENEKLERİN:
- Kullanıcılar PDF yükleyerek seni eğitebilir (fine-tuning)
- Ders kitapları, dökümanlar yüklenince o bilgileri öğrenirsin
- Yüklenen her belge ile bilgi tabanın genişler
- Hem genel bilgilerini hem de yüklenen belge bilgilerini kullanırsın

`

  if (context && context.length > 0) {
    prompt += `YÜKLENEN BELGEDEN BİLGİLER:
${context}

ÖNEMLI: SADECE bu belgedeki bilgileri kullan. Belgede yoksa söyle.\n\n`
  } else {
    prompt += `ŞU AN: Henüz belge yüklenmedi. Genel bilgilerimi kullanıyorum. Kullanıcı PDF yükleyerek beni eğitebilir.\n\n`
  }

  if (chatHistory && chatHistory.length > 0) {
    prompt += `GEÇMİŞ KONUŞMA:\n`
    chatHistory.slice(-10).forEach((msg: any) => {
      prompt += `${msg.role === "user" ? "Kullanıcı" : "Asistan"}: ${msg.content}\n`
    })
    prompt += "\n"
  }

  prompt += `Kullanıcı: ${message}\nAsistan:`

  const result = await model.generateContent(prompt)
  const response = await result.response
  return response.text()
}

export async function POST(req: NextRequest) {
  try {
    const { message, chatHistory, context } = await req.json()

    if (!message) {
      return NextResponse.json({ error: "Mesaj gerekli" }, { status: 400 })
    }

    const provider = selectProvider()
    console.log(`[v0] Using provider: ${provider}`)

    let responseText: string

    try {
      if (provider === "mistral") {
        responseText = await callMistral(message, chatHistory || [], context)
        dailyUsage.mistral++
      } else {
        responseText = await callGemini(message, chatHistory || [], context)
        dailyUsage.gemini++
      }
    } catch (error: any) {
      console.error(`[v0] ${provider} failed, trying fallback...`, error)

      const fallbackProvider = provider === "mistral" ? "gemini" : "mistral"
      console.log(`[v0] Fallback to: ${fallbackProvider}`)

      if (fallbackProvider === "mistral") {
        responseText = await callMistral(message, chatHistory || [], context)
        dailyUsage.mistral++
      } else {
        responseText = await callGemini(message, chatHistory || [], context)
        dailyUsage.gemini++
      }
    }

    return NextResponse.json({
      response: responseText,
      provider,
      usage: dailyUsage,
    })
  } catch (error: any) {
    console.error("[v0] Chat API error:", error)
    return NextResponse.json({ error: error.message || "Bir hata oluştu" }, { status: 500 })
  }
}
