import GenerateFlow from "@/components/GenerateFlow";

export default function GeneratePage({
  searchParams,
}: {
  searchParams: { topic?: string };
}) {
  return (
    <div className="max-w-2xl mx-auto px-6 py-16">
      <h1 className="font-display text-2xl md:text-3xl font-semibold text-ink">
        Set up the run
      </h1>
      <p className="text-muted mt-2 mb-8">
        The crew works through research, writing, editing, SEO, image, and
        social in order — usually a minute or two, start to finish.
      </p>
      <GenerateFlow initialTopic={searchParams.topic} />
    </div>
  );
}