import { type NextRequest, NextResponse } from "next/server"
import { GoogleGenerativeAI } from "@google/generative-ai"

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "")

export async function POST(req: NextRequest) {
  try {
    console.log("[v0] Extract text endpoint called")

    if (!process.env.GEMINI_API_KEY) {
      console.error("[v0] Missing GEMINI_API_KEY")
      return NextResponse.json(
        {
          error:
            "GEMINI_API_KEY environment variable eksik. Lütfen Vercel Dashboard → Settings → Environment Variables'dan ekleyin.",
        },
        { status: 500 },
      )
    }

    const { blobUrl, fileName } = await req.json()

    if (!blobUrl || !fileName) {
      console.error("[v0] Missing blobUrl or fileName")
      return NextResponse.json({ error: "Blob URL ve dosya adı gerekli" }, { status: 400 })
    }

    if (!fileName.endsWith(".pdf")) {
      console.error("[v0] File is not PDF:", fileName)
      return NextResponse.json({ error: "Sadece PDF dosyaları yüklenebilir" }, { status: 400 })
    }

    console.log("[v0] Processing PDF from Blob:", fileName)

    let base64
    try {
      console.log("[v0] Downloading PDF from Blob...")
      const response = await fetch(blobUrl)
      if (!response.ok) {
        throw new Error(`Blob indirme hatası: ${response.status}`)
      }
      const arrayBuffer = await response.arrayBuffer()
      const buffer = Buffer.from(arrayBuffer)
      base64 = buffer.toString("base64")
      console.log("[v0] PDF converted to base64, length:", base64.length)
    } catch (downloadError: any) {
      console.error("[v0] Blob download error:", downloadError)
      return NextResponse.json(
        {
          error: "PDF indirme hatası",
          details: downloadError.message || downloadError.toString(),
        },
        { status: 500 },
      )
    }

    let extractedText
    try {
      console.log("[v0] Calling Gemini API for text extraction...")
      const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" })

      const result = await model.generateContent([
        {
          inlineData: {
            mimeType: "application/pdf",
            data: base64,
          },
        },
        "Bu PDF dosyasındaki tüm metni çıkar. Başlıklar, paragraflar ve önemli bilgileri koru. Sadece metni ver, açıklama yapma.",
      ])

      const geminiResponse = await result.response
      extractedText = geminiResponse.text()
      console.log("[v0] Gemini extraction successful, text length:", extractedText.length)
    } catch (geminiError: any) {
      console.error("[v0] Gemini API error:", geminiError)
      return NextResponse.json(
        {
          error: "Gemini API hatası",
          details: geminiError.message || geminiError.toString(),
          hint: "API key'inizi https://ai.google.dev adresinde 'Get API Key' ile oluşturun ve Vercel Dashboard → Settings → Environment Variables'a ekleyin.",
        },
        { status: 500 },
      )
    }

    if (!extractedText || extractedText.length < 50) {
      console.error("[v0] Insufficient text extracted:", extractedText?.length || 0)
      throw new Error("PDF'den yeterli metin çıkarılamadı. Dosyanın metin içerdiğinden emin olun.")
    }

    console.log("[v0] PDF processing completed successfully")
    return NextResponse.json({
      success: true,
      fileName,
      blobUrl,
      extractedText,
      textLength: extractedText.length,
    })
  } catch (error: any) {
    console.error("[v0] Unexpected error:", error)
    console.error("[v0] Error stack:", error.stack)
    return NextResponse.json(
      {
        error: error.message || "PDF işleme hatası",
        details: error.toString(),
      },
      { status: 500 },
    )
  }
}
