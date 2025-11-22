import { type NextRequest, NextResponse } from "next/server"
import { put } from "@vercel/blob"
import { GoogleGenerativeAI } from "@google/generative-ai"

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "")

export async function POST(req: NextRequest) {
  try {
    console.log("[v0] Upload PDF endpoint called")

    if (!process.env.GEMINI_API_KEY && !process.env.OPENROUTER_API_KEY) {
      console.error("[v0] Missing API keys")
      return NextResponse.json(
        {
          error:
            "API anahtarı eksik. Lütfen Vercel Dashboard → Settings → Environment Variables'dan GEMINI_API_KEY veya OPENROUTER_API_KEY ekleyin.",
        },
        { status: 500 },
      )
    }

    console.log("[v0] API keys present:", {
      hasGemini: !!process.env.GEMINI_API_KEY,
      hasOpenRouter: !!process.env.OPENROUTER_API_KEY,
    })

    const formData = await req.formData()
    const file = formData.get("file") as File

    if (!file) {
      console.error("[v0] No file in form data")
      return NextResponse.json({ error: "Dosya bulunamadı" }, { status: 400 })
    }

    if (!file.name.endsWith(".pdf")) {
      console.error("[v0] File is not PDF:", file.name)
      return NextResponse.json({ error: "Sadece PDF dosyaları yüklenebilir" }, { status: 400 })
    }

    const maxSize = 100 * 1024 * 1024 // 100MB
    if (file.size > maxSize) {
      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2)
      console.error("[v0] File too large:", fileSizeMB, "MB")
      return NextResponse.json(
        { error: `PDF dosyası çok büyük (${fileSizeMB}MB). Maksimum 100MB olmalı.` },
        { status: 400 },
      )
    }

    console.log("[v0] Processing PDF:", file.name, `(${(file.size / (1024 * 1024)).toFixed(2)}MB)`)

    let blob
    try {
      console.log("[v0] Uploading to Vercel Blob...")
      blob = await put(file.name, file, {
        access: "public",
      })
      console.log("[v0] Blob upload successful:", blob.url)
    } catch (blobError: any) {
      console.error("[v0] Blob upload error:", blobError)
      return NextResponse.json(
        {
          error: "Dosya yükleme hatası",
          details: blobError.message || blobError.toString(),
        },
        { status: 500 },
      )
    }

    let base64
    try {
      console.log("[v0] Downloading PDF from Blob...")
      const response = await fetch(blob.url)
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

    if (!process.env.GEMINI_API_KEY) {
      console.log("[v0] No Gemini API key, returning basic info")
      return NextResponse.json({
        success: true,
        fileName: file.name,
        blobUrl: blob.url,
        extractedText: `PDF yüklendi: ${file.name}. PDF içeriğini işlemek için GEMINI_API_KEY gerekli.`,
        textLength: 0,
      })
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
      fileName: file.name,
      blobUrl: blob.url,
      extractedText,
      textLength: extractedText.length,
    })
  } catch (error: any) {
    console.error("[v0] Unexpected error:", error)
    console.error("[v0] Error stack:", error.stack)
    return NextResponse.json(
      {
        error: error.message || "PDF yükleme hatası",
        details: error.toString(),
        stack: error.stack,
      },
      { status: 500 },
    )
  }
}
