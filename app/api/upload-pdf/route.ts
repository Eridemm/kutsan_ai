import { type NextRequest, NextResponse } from "next/server"
import { writeFile, mkdir } from "fs/promises"
import { existsSync } from "fs"
import path from "path"

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData()
    const file = formData.get("file") as File

    if (!file) {
      return NextResponse.json({ error: "Dosya bulunamadı" }, { status: 400 })
    }

    if (!file.name.endsWith(".pdf")) {
      return NextResponse.json({ error: "Sadece PDF dosyaları yüklenebilir" }, { status: 400 })
    }

    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)

    // Save to public/uploads directory
    const uploadsDir = path.join(process.cwd(), "public", "uploads")
    if (!existsSync(uploadsDir)) {
      await mkdir(uploadsDir, { recursive: true })
    }

    const fileName = `${Date.now()}-${file.name}`
    const filePath = path.join(uploadsDir, fileName)
    await writeFile(filePath, buffer)

    return NextResponse.json({
      success: true,
      fileName,
      filePath: `/uploads/${fileName}`,
    })
  } catch (error: any) {
    console.error("[v0] Upload error:", error)
    return NextResponse.json({ error: error.message || "Yükleme hatası" }, { status: 500 })
  }
}
