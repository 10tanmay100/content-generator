import HeroPromptBar from "@/components/HeroPromptBar";
import AgentRelay from "@/components/AgentRelay";

export default function HomePage() {
  return (
    <div>
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-16 text-center">
        <h1 className="font-display text-4xl md:text-5xl font-semibold text-ink leading-[1.1]">
          Six agents. One topic. A finished draft.
        </h1>
        <p className="mt-5 text-muted text-base md:text-lg max-w-xl mx-auto leading-relaxed">
          Type a topic below. Six agents — every one powered by Claude Sonnet —
          research it, write it, edit it, score it for SEO, illustrate it,
          and repurpose it for social, one after another.
        </p>

        <div className="mt-10">
          <HeroPromptBar />
        </div>
      </section>

      <section className="pb-24">
        <AgentRelay />
      </section>

      <section className="max-w-3xl mx-auto px-6 pb-20 grid sm:grid-cols-3 gap-8 text-sm">
        <div>
          <p className="text-ink font-medium">Powered by Claude Sonnet</p>
          <p className="text-muted mt-1 leading-relaxed">
            Every agent runs on Anthropic's Claude Sonnet — reliable tool
            use and strong long-form writing, no model server to babysit.
          </p>
        </div>
        <div>
          <p className="text-ink font-medium">Real output, not a demo</p>
          <p className="text-muted mt-1 leading-relaxed">
            A publish-ready Markdown article, a generated hero image, and
            three social variants — every run.
          </p>
        </div>
        <div>
          <p className="text-ink font-medium">Ready for Azure</p>
          <p className="text-muted mt-1 leading-relaxed">
            Jobs persist to Cosmos DB and the whole stack ships to Azure
            Container Apps when you're ready to go live.
          </p>
        </div>
      </section>
    </div>
  );
}