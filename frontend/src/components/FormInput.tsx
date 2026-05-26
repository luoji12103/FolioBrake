interface FormInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
}

export function FormInput({ label, value, onChange, placeholder, type = "text" }: FormInputProps) {
  return (
    <div className="form-group">
      <label>{label}</label>
      <input
        className="form-input"
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}
