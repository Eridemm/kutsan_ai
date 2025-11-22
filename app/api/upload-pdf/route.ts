import { type NextRequest, NextResponse } from "next/server"
import { GoogleGenerativeAI } from "@google/generative-ai"

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "")

export async function POST(req: NextRequest) {
  try {
    if (!process.env.GEMINI_API_KEY) {
      return NextResponse.json(
        { error: "GEMINI_API_KEY environment variable eksik. Lütfen API key'inizi ekleyin." },
        { status: 500 },
      )
    }

    const formData = await req.formData()
    const file = formData.get("file") as File

    if (!file) {
      return NextResponse.json({ error: "Dosya bulunamadı" }, { status: 400 })
    }

    if (!file.name.endsWith(".pdf")) {
      return NextResponse.json({ error: "Sadece PDF dosyaları yüklenebilir" }, { status: 400 })
    }

    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      return NextResponse.json({ error: "PDF dosyası çok büyük. Maksimum 10MB olmalı." }, { status: 400 })
    }

    console.log("[v0] Processing PDF:", file.name, file.size, "bytes")

    // Convert file to base64
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    const base64 = buffer.toString("base64")

    // Use Gemini to extract text from PDF
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash-exp" })

    const result = await model.generateContent([
      {
        inlineData: {
          mimeType: "application/pdf",
          data: base64,
        },
      },
      "Bu PDF dosyasındaki tüm metni çıkar. Başlıklar, paragraflar ve önemli bilgileri koru. Sadece metni ver, açıklama yapma.",
    ])

    const response = await result.response
    const extractedText = response.text()

    console.log("[v0] Extracted text length:", extractedText.length)

    if (!extractedText || extractedText.length < 50) {
      throw new Error("PDF'den yeterli metin çıkarılamadı. Dosyanın metin içerdiğinden emin olun.")
    }

    return NextResponse.json({
      success: true,
      fileName: file.name,
      extractedText,
      textLength: extractedText.length,
    })
  } catch (error: any) {
    console.error("[v0] Upload error:", error)
    return NextResponse.json(
      {
        error: error.message || "PDF yükleme hatası",
        details: error.toString(),
      },
      { status: 500 },
    )
  }
}
