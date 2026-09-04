export default function FormField({ id, label, error, ...inputProps }) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <input id={id} name={id} required aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined} {...inputProps} />
      {error && <p className="field-error" id={`${id}-error`}>{error}</p>}
    </div>
  )
}
