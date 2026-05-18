"use client";

import { useState, useCallback, useEffect } from "react";
import { Upload, FileText, Trash2, CheckCircle, Database, Play } from "lucide-react";

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

  const loadDefaultDocuments = async () => {
    setUploadStatus([{ file: "Loading default documents...", status: "uploading" }]);

    try {
      const response = await fetch("http://localhost:8000/load-default", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to load default documents");
      }

      const data = await response.json();

      setUploadStatus(
        data.files_processed.map((f: string) => ({
          file: f,
          status: "success" as const,
          message: "Indexed",
        }))
      );

      setDocCount(data.total_chunks);
    } catch (error) {
      setUploadStatus([{ file: "Failed to load defaults", status: "error", message: "Error" }]);
    }
  };

  const [testResults, setTestResults] = useState<{total: number; passed: number; failed: number; allPassed: boolean} | null>(null);
  const [sampleQuestions, setSampleQuestions] = useState<string[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  useEffect(() => {
    // Load questions once on mount
    fetch("http://localhost:8000/test-questions")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setSampleQuestions(data);
        }
      })
      .catch((err) => console.error("Failed to load questions:", err));
  }, []);

  const loadSampleQuestion = async () => {
    if (sampleQuestions.length === 0) {
      console.error("No sample questions loaded");
      return;
    }

    // Check if input is empty by dispatching an event that Chat component will respond to
    window.dispatchEvent(new CustomEvent('checkInputEmpty', { detail: {
      callback: (isEmpty: boolean) => {
        if (isEmpty) {
          // Cycle to next question only if input is empty
          const question = sampleQuestions[currentQuestionIndex];
          setCurrentQuestionIndex((prev) => (prev + 1) % sampleQuestions.length);
          window.dispatchEvent(new CustomEvent('loadSampleQuestion', { detail: question }));
        }
      }
    }}));
  };

  const [testProgress, setTestProgress] = useState<{total: number; current: number; passed: number; failed: number} | null>(null);
  const [isTestRunning, setIsTestRunning] = useState(false);

  const runTest = async () => {
    setIsTestRunning(true);
    setTestProgress(null);

    try {
      // Start the test
      const startResponse = await fetch("http://localhost:8000/run-test-start", {
        method: "POST",
      });

      if (!startResponse.ok) {
        throw new Error("Failed to start test");
      }

      const startData = await startResponse.json();
      setTestProgress({ total: startData.total_questions, current: 0, passed: 0, failed: 0 });

      // Run questions one at a time
      let complete = false;
      while (!complete) {
        const nextResponse = await fetch("http://localhost:8000/run-test-next", {
          method: "POST",
        });

        if (!nextResponse.ok) {
          console.error("Test next failed:", await nextResponse.text());
          break;
        }

        const data = await nextResponse.json();
        console.log("Test progress:", data);

        // Check for completion first - if complete, don't try to update with undefined data
        if (data.status === "complete") {
          console.log("Test complete detected");
          // Update final progress before breaking
          setTestProgress({
            total: data.total,
            current: data.current,
            passed: data.passed,
            failed: data.failed,
          });
          complete = true;
          break;
        }

        // Update progress display for running state
        setTestProgress({
          total: data.total,
          current: data.current,
          passed: data.passed,
          failed: data.failed,
        });

        // Update status with current progress (only if we have a question)
        if (data.question) {
          setUploadStatus([{
            file: `Q${data.current}/${data.total}: ${data.question.substring(0, 40)}...`,
            status: data.passed_this ? "success" : "error",
            message: data.passed_this ? "Passed" : "Failed"
          }]);
        }
      }

      // Use the final data directly, not the stale testProgress state
      const finalData = await fetch("http://localhost:8000/run-test-status").then(r => r.json());

      setTestResults({
        total: finalData.total,
        passed: finalData.passed,
        failed: finalData.failed,
        allPassed: finalData.failed === 0,
      });

      setUploadStatus([{
        file: `Test ${finalData.failed === 0 ? 'PASSED' : 'FAILED'}: ${finalData.passed}/${finalData.total} questions passed`,
        status: finalData.failed === 0 ? "success" : "error",
        message: finalData.failed === 0 ? "All questions answered" : `${finalData.failed} failed`
      }]);
    } catch (error) {
      setUploadStatus([{ file: "Test execution failed", status: "error", message: "Error" }]);
    } finally {
      setIsTestRunning(false);
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

      <button
        onClick={loadDefaultDocuments}
        className="mt-3 w-full py-2 px-4 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
      >
        <Database size={16} />
        Load Default Documents
      </button>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <button
          onClick={runTest}
          disabled={isTestRunning}
          className="py-2 px-4 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Play size={16} />
          {isTestRunning ? 'Running...' : 'Run Test'}
        </button>
        <button
          onClick={loadSampleQuestion}
          className="py-2 px-4 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
        >
          <FileText size={16} />
          Load Sample Question
        </button>
      </div>

      {testProgress && isTestRunning && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-zinc-600 dark:text-zinc-400 mb-1">
            <span>Progress: {testProgress.current}/{testProgress.total}</span>
            <span className="text-green-600">{testProgress.passed} passed</span>
            {testProgress.failed > 0 && <span className="text-red-600">{testProgress.failed} failed</span>}
          </div>
          <div className="w-full bg-zinc-200 dark:bg-zinc-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(testProgress.current / testProgress.total) * 100}%` }}
            />
          </div>
        </div>
      )}

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
