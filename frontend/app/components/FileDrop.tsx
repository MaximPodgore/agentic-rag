"use client";

import { useState, useCallback, useEffect } from "react";
import { Upload, FileText, Trash2, CheckCircle } from "lucide-react";

interface UploadStatus {
  file: string;
  status: "pending" | "uploading" | "success" | "error";
  message?: string;
}

export function FileDrop() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus[]>([]);
  const [docCount, setDocCount] = useState<number | null>(null);

  const checkHealth = async () => {
    try {
      const response = await fetch("http://localhost:8000/health");
      if (response.ok) {
        const data = await response.json();
        setDocCount(data.documents_indexed);
      }
    } catch (error) {
      console.error("Health check failed:", error);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const uploadFiles = async (files: File[]) => {
    const validFiles = files.filter(
      (f) => f.name.endsWith(".md") || f.name.endsWith(".txt") || f.name.endsWith(".pdf")
    );

    if (validFiles.length === 0) {
      alert("Please upload .md, .txt, or .pdf files only");
      return;
    }

    const formData = new FormData();
    validFiles.forEach((file) => {
      formData.append("files", file);
      setUploadStatus((prev) => [
        ...prev,
        { file: file.name, status: "uploading" },
      ]);
    });

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();

      setUploadStatus((prev) =>
        prev.map((s) =>
          validFiles.some((f) => f.name === s.file)
            ? { file: s.file, status: "success", message: `Indexed` }
            : s
        )
      );

      setDocCount(data.total_chunks);
    } catch (error) {
      setUploadStatus((prev) =>
        prev.map((s) =>
          validFiles.some((f) => f.name === s.file)
            ? { file: s.file, status: "error", message: "Upload failed" }
            : s
        )
      );
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    uploadFiles(files);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      uploadFiles(files);
    }
  };

  const clearDocuments = async () => {
    try {
      const response = await fetch("http://localhost:8000/clear", {
        method: "POST",
      });
      if (response.ok) {
        setUploadStatus([]);
        setDocCount(0);
      }
    } catch (error) {
      console.error("Failed to clear documents:", error);
    }
  };

  return (
    <div className="h-full flex flex-col p-4">
      <div className="mb-4">
        <h2 className="font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <FileText size={18} />
          Documents
        </h2>
        {docCount !== null && (
          <p className="text-sm text-zinc-500 mt-1">{docCount} chunks indexed</p>
        )}
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          isDragging
            ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
            : "border-zinc-300 dark:border-zinc-600 hover:border-zinc-400 dark:hover:border-zinc-500"
        }`}
      >
        <Upload className="mx-auto h-8 w-8 text-zinc-400 mb-2" />
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Drag and drop files here
        </p>
        <p className="text-xs text-zinc-500 mt-1">.md, .txt, and .pdf files</p>

        <label className="mt-3 inline-block">
          <input
            type="file"
            multiple
            accept=".md,.txt,.pdf"
            onChange={handleFileSelect}
            className="hidden"
          />
          <span className="text-sm text-blue-600 hover:text-blue-700 cursor-pointer">
            or click to browse
          </span>
        </label>
      </div>

      {uploadStatus.length > 0 && (
        <div className="mt-4 flex-1 overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
              Uploaded Files
            </h3>
            <button
              onClick={clearDocuments}
              className="text-xs text-red-600 hover:text-red-700 flex items-center gap-1"
            >
              <Trash2 size={12} />
              Clear All
            </button>
          </div>

          <ul className="space-y-2">
            {uploadStatus.map((file, idx) => (
              <li
                key={`${file.file}-${idx}`}
                className="flex items-center justify-between text-sm p-2 bg-zinc-100 dark:bg-zinc-800 rounded"
              >
                <div className="flex items-center gap-2 truncate">
                  <FileText size={14} className="text-zinc-500 flex-shrink-0" />
                  <span className="truncate text-zinc-700 dark:text-zinc-300">
                    {file.file}
                  </span>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {file.status === "uploading" && (
                    <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  )}
                  {file.status === "success" && (
                    <CheckCircle size={16} className="text-green-600" />
                  )}
                  {file.status === "error" && (
                    <span className="text-xs text-red-600">{file.message}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
