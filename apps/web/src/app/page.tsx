export default function HomePage() {
  return (
    <main id="main-content" className="shell">
      <header>
        <p className="eyebrow">Private Windows support</p>
        <h1>Hello, I’m DeskPilot.</h1>
        <p>How can I help you today?</p>
      </header>
      <section aria-labelledby="support-heading" className="panel">
        <h2 id="support-heading">Start a support conversation</h2>
        <form>
          <label htmlFor="issue">Describe the issue on your Windows 10 or 11 PC</label>
          <textarea id="issue" name="issue" rows={5} required aria-describedby="privacy-note" />
          <p id="privacy-note">Do not enter passwords. Remote access is never started without your permission.</p>
          <button type="submit">Continue</button>
        </form>
      </section>
    </main>
  );
}
