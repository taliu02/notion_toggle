// import Image from "next/image";
import FileUpload from "../components/FileUpload";

export default function Home() {
  return (
    <main className="min-h-screen p-24">
      <h1 className="text-4xl font-bold text-center mb-8">
        PowerPoint to Notion Converter
      </h1>
      <FileUpload />
    </main>
  );
}
