// app/components/FileUpload.tsx
"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
// import Converter from "@hckrnews/ppt2pdf";

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFile(acceptedFiles[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.ms-powerpoint": [".ppt"],
      "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        [".pptx"],
    },
    multiple: false,
  });

  // const handleUpload = async () => {
  //   if (!file) return;

  //   try {
  //     // First convert PPT to PDF

  //     const converter = Converter.create({
  //       file: URL.createObjectURL(file),
  //       output: "/tmp/", // Temporary output directory
  //     });

  //     const pdfResult = await converter.convertPptToPdf();

  //     // Create FormData with converted PDF
  //     const formData = new FormData();
  //     formData.append("file", pdfResult); // Append the converted PDF

  //     // Upload to your API
  //     const response = await fetch("/api/upload", {
  //       method: "POST",
  //       body: formData,
  //     });
  //     const data = await response.json();
  //     console.log(data);
  //   } catch (error) {
  //     console.error("Error during conversion or upload:", error);
  //   }
  // };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/upload", {
        method: "POST",
        headers: {
          // Don't set Content-Type header when using FormData
          // FormData automatically sets the correct Content-Type with boundary
          Accept: "application/json",
        },
        body: formData,
      });
      // const data = await response.json();
      // console.log(data);
    } catch (error) {
      console.error("Error uploading file:", error);
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-10">
      <div
        {...getRootProps()}
        className={`p-10 border-2 border-dashed rounded-lg text-center
          ${isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300"}`}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the PowerPoint file here...</p>
        ) : (
          <p>Drag and drop a PowerPoint file here, or click to select file</p>
        )}
      </div>

      {file && (
        <div className="mt-4">
          <p>Selected file: {file.name}</p>
          <button
            onClick={handleUpload}
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Upload to Notion
          </button>
        </div>
      )}
    </div>
  );
}
