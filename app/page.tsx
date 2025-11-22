"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Spinner } from "@/components/ui/spinner"
import { Upload, Send, Trash2 } from "lucide-react"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
  thinkingTime?: number
  provider?: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [thinkingTime, setThinkingTime] = useState(0)
  const [uploadedPdf, setUploadedPdf] = useState<string | null>(null)
  const [pdfContext, setPdfContext] = useState<string>("")
  const [currentProvider, setCurrentProvider] = useState<string>("mistral")
  const scrollRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  useEffect(() => {
    if (isLoading && timerRef.current === null) {
      timerRef.current = setInterval(() => {
        setThinkingTime((prev) => prev + 1)
      }, 1000)
    } else if (!isLoading && timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [isLoading])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)
    setThinkingTime(0)

    const startTime = Date.now()

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          chatHistory: messages.slice(-10),
          context: pdfContext,
        }),
      })

      const data = await response.json()
      const endTime = Date.now()
      const totalTime = Math.round((endTime - startTime) / 1000)

      if (data.error) {
        throw new Error(data.error)
      }

      setCurrentProvider(data.provider || "unknown")

      const assistantMessage: Message = {
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
        thinkingTime: totalTime,
        provider: data.provider,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      console.error("[v0] Send error:", error)
      const errorMessage: Message = {
        role: "assistant",
        content: `Hata: ${error.message}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      setThinkingTime(0)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2)
    console.log(`[v0] Uploading PDF: ${file.name} (${fileSizeMB}MB)`)

    const progressMessage: Message = {
      role: "assistant",
      content: `📤 PDF yükleniyor: ${file.name} (${fileSizeMB}MB)\n\nLütfen bekleyin...`,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, progressMessage])

    setIsLoading(true)

    try {
      console.log("[v0] Uploading to Blob Storage...")
      const blobResponse = await fetch(`/api/upload-pdf/blob?filename=${encodeURIComponent(file.name)}`, {
        method: "POST",
        body: file,
      })

      if (!blobResponse.ok) {
        const errorText = await blobResponse.text()
        console.error("[v0] Blob upload error:", errorText)
        throw new Error(`Blob yükleme hatası: ${errorText}`)
      }

      const { url: blobUrl } = await blobResponse.json()
      console.log("[v0] Blob upload successful:", blobUrl)

      console.log("[v0] Extracting text from PDF...")
      const response = await fetch("/api/upload-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          blobUrl,
          fileName: file.name,
        }),
      })

      if (!response.ok) {
        const text = await response.text()
        console.error("[v0] Extract error response:", text)

        let errorMessage = `PDF işleme başarısız (${response.status})`
        try {
          const errorData = JSON.parse(text)
          errorMessage = errorData.error || errorMessage
        } catch {
          errorMessage = text.substring(0, 200)
        }

        throw new Error(errorMessage)
      }

      let data
      try {
        data = await response.json()
      } catch (parseError) {
        console.error("[v0] JSON parse error:", parseError)
        throw new Error("Sunucudan geçersiz yanıt alındı. Lütfen tekrar deneyin.")
      }

      if (data.error) {
        throw new Error(data.error)
      }

      setUploadedPdf(data.fileName)
      setPdfContext(data.extractedText || "")

      const successMessage: Message = {
        role: "assistant",
        content: `✅ PDF başarıyla yüklendi: ${data.fileName}\n\n${data.textLength.toLocaleString()} karakter metin çıkarıldı. Artık bu belgeye dayalı sorular sorabilirsiniz!`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, successMessage])
    } catch (error: any) {
      console.error("[v0] Upload error:", error)
      const errorMessage: Message = {
        role: "assistant",
        content: `❌ PDF yükleme hatası: ${error.message}`,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      e.target.value = ""
    }
  }

  const handleClearPdf = () => {
    setUploadedPdf(null)
    setPdfContext("")

    const clearMessage: Message = {
      role: "assistant",
      content: "PDF kaldırıldı. Artık genel bilgilerimi kullanıyorum.",
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, clearMessage])
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-4xl mx-auto h-[calc(100vh-2rem)] flex flex-col gap-4">
        <Card className="shadow-lg">
          <CardHeader className="pb-3">
            <CardTitle className="text-2xl font-bold text-center bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              AI Chatbot ({currentProvider === "mistral" ? "Mistral 24B" : "Gemini 2.0"})
            </CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-3 pb-4">
            <label htmlFor="pdf-upload">
              <Button variant="outline" className="cursor-pointer bg-transparent" asChild disabled={isLoading}>
                <span>
                  <Upload className="w-4 h-4 mr-2" />
                  PDF Yükle
                </span>
              </Button>
            </label>
            <input
              id="pdf-upload"
              type="file"
              accept=".pdf"
              onChange={handleUpload}
              className="hidden"
              disabled={isLoading}
            />
            {uploadedPdf && (
              <div className="flex items-center gap-2 flex-1">
                <span className="text-sm text-muted-foreground truncate">{uploadedPdf}</span>
                <Button variant="ghost" size="sm" onClick={handleClearPdf} className="shrink-0" disabled={isLoading}>
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="flex-1 shadow-lg flex flex-col min-h-0">
          <ScrollArea className="flex-1 p-4 overflow-y-auto" ref={scrollRef}>
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-muted-foreground">
                Merhaba! Size nasıl yardımcı olabilirim?
              </div>
            ) : (
              <div className="space-y-4 pb-4">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        msg.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-slate-100 dark:bg-slate-800 text-foreground"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      {msg.thinkingTime !== undefined && (
                        <p className="text-xs mt-2 opacity-70">
                          {msg.thinkingTime} saniye düşünüldü
                          {msg.provider && ` • ${msg.provider === "mistral" ? "Mistral" : "Gemini"}`}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-slate-100 dark:bg-slate-800 rounded-lg p-3 flex items-center gap-2">
                      <Spinner className="w-4 h-4" />
                      <span>Düşünüyor... {thinkingTime}s</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </ScrollArea>

          <div className="p-4 border-t bg-background shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault()
                handleSend()
              }}
              className="flex gap-2"
            >
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Mesajınızı yazın..."
                disabled={isLoading}
                className="flex-1"
              />
              <Button type="submit" disabled={isLoading || !input.trim()}>
                <Send className="w-4 h-4" />
              </Button>
            </form>
          </div>
        </Card>
      </div>
    </div>
  )
}
