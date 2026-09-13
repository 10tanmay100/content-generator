import ContentForm from "@/components/ContentForm";

export default function GeneratePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Generate content</h1>
      <p className="text-gray-500 mb-6">Kick off the research → write → edit → SEO → image → social crew.</p>
      <ContentForm />
    </div>
  );
}
