interface FormTextareaProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
}

export function FormTextarea({ label, value, onChange, placeholder, rows = 4 }: FormTextareaProps) {
  return (
    <div className="form-group">
      <label>{label}</label>
      <textarea
        className="form-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
      />
    </div>
  );
}
