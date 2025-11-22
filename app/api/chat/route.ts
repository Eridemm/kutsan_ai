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
    ? `Sen Türkçe konuşan yardımcı bir AI asistansın. Aşağıdaki belge içeriğine dayalı cevap ver:\n\n${context}\n\nSADECE belgede olan bilgileri kullan. Bilmiyorsan "Bu bilgi belgede yok" de.`
    : "Sen Türkçe konuşan yardımcı bir AI asistansın. Sorulara net, doğru ve Türkçe cevap ver."

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

  let prompt = `Sen Türkçe konuşan yardımsever bir asistansın. Sorulara net, doğru ve Türkçe cevap veriyorsun.

KURALLAR:
1. SADECE TÜRKÇE cevap ver, başka dil kullanma
2. Eğer context verilmişse, SADECE o bilgileri kullan
3. Context'te bilgi yoksa genel bilgini kullan ama bunu belirt
4. Kısa ve öz cevaplar ver
5. Yarıda kesme, cümleyi tamamla\n\n`

  if (context && context.length > 0) {
    prompt += `BELGEDEN BİLGİLER:\n${context}\n\n`
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
