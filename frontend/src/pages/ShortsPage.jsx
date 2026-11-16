import { shortsFrame } from "../shorts";

export function ShortsPage() {
  const frame = shortsFrame();
  return (
    <section className="shorts">
      <div className="shorts__stage">
        <h1>{frame.empty}</h1>
      </div>
    </section>
  );
}
