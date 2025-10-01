type Props = {
  choices: string[];
  onChoose: (text: string) => void;
  disabled?: boolean;
};

export default function ChoiceButtons({ choices, onChoose, disabled }: Props) {
  if (!choices?.length) return null;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 }}>
      {choices.map((c, i) => (
        <button
          key={i}
          className="chipBtn"
          onClick={() => onChoose(c)}
          disabled={disabled}
          title={c}
        >
          {c}
        </button>
      ))}
    </div>
  );
}
