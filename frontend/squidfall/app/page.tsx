import { CopilotSidebar } from "@copilotkit/react-core/v2";

const PROMPTS = [
  { ico: "🌤️", text: "What's the weather in Pittsburgh, PA?" },
  { ico: "🌧️", text: "Will it rain tomorrow in Seattle?" },
  { ico: "❄️", text: "How cold is it in Anchorage right now?" },
  { ico: "🌪️", text: "Forecast for Miami this weekend" },
];

export default function Home() {
  return (
    <>
      <section className="hero glass">
        <h1>Ask the sky.</h1>
        <p className="tag">
          Squidfall is a liquid-glass weather agent. Name a place and it geocodes
          the location, then pulls a live forecast straight from the National
          Weather Service.
        </p>

        <div className="chips">
          {PROMPTS.map((p) => (
            <span className="chip" key={p.text}>
              <span className="ico">{p.ico}</span>
              {p.text}
            </span>
          ))}
        </div>

        <div className="hint">
          <span className="dot" />
          Open the assistant (bottom-right) and ask away.
        </div>

        <div className="foot">
          Powered by <code>LangGraph</code> + <code>Ollama·Qwen</code> · tools over{" "}
          <code>MCP</code>
        </div>
      </section>

      <CopilotSidebar />
    </>
  );
}
