const steps = [
  { id: "outline", label: "Outline" },
  { id: "chapters", label: "Chapters" },
  { id: "final", label: "Final" }
];

function Pipeline({ stage }) {
  return (
    <div className="pipeline">
      {steps.map((step, index) => (
        <div key={step.id} className="pipeline-item">
          <div className={`pipeline-step ${stage === step.id ? "active" : ""}`}>{step.label}</div>
          {index < steps.length - 1 ? <div className="pipeline-arrow">&gt;</div> : null}
        </div>
      ))}
    </div>
  );
}

export default Pipeline;
