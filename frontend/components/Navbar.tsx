import Link from "next/link";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-edge bg-canvas/80 backdrop-blur-md">
      <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="font-display font-semibold text-ink tracking-tight">
          Content Pipeline
        </Link>
        <nav className="text-sm">
          <Link
            href="/generate"
            className="text-muted hover:text-ink transition-colors"
          >
            New generation
          </Link>
        </nav>
      </div>
    </header>
  );
}
