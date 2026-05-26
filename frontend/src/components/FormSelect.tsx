interface FormSelectProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}

export function FormSelect({ label, value, onChange, options }: FormSelectProps) {
  return (
    <div className="form-group">
      <label>{label}</label>
      <select className="form-input" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
      </select>
    </div>
  );
}
