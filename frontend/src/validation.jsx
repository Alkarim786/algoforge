import { useState } from "react";

/* Readable form checks. Forms use noValidate, so the browser's own bubbles ("Please match the requested
   format.") never appear; these messages are shown in the page instead. A field can override a message with
   data-pattern-message or data-required-message, and name itself with data-label. */

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function labelOf(element) {
  if (element.dataset.label) return element.dataset.label;
  const label = (element.id && document.querySelector(`label[for="${CSS.escape(element.id)}"]`)) || element.closest("label");
  const text = label ? [...label.childNodes].filter((node) => node.nodeType === Node.TEXT_NODE).map((node) => node.textContent).join(" ").trim() : "";
  return text || element.getAttribute("aria-label") || element.placeholder || "This field";
}

/** The problem with one field, as a sentence, or null when it's fine. */
export function fieldProblem(element) {
  if (!element.willValidate || ["submit", "button", "reset", "hidden"].includes(element.type)) return null;
  const value = element.type === "checkbox" ? (element.checked ? "on" : "") : element.value ?? "";
  const label = labelOf(element);
  if (element.required && !value.trim()) return element.dataset.requiredMessage || `${label} is required.`;
  if (!value) return null;
  if (element.type === "email" && !EMAIL.test(value)) return "Enter an email address like name@example.com.";
  if (element.minLength > 0 && value.length < element.minLength) return `${label} needs at least ${element.minLength} characters.`;
  if (element.maxLength > 0 && value.length > element.maxLength) return `${label} can be at most ${element.maxLength} characters.`;
  if (element.pattern && !new RegExp(`^(?:${element.pattern})$`, "u").test(value)) {
    return element.dataset.patternMessage || `${label} isn't in the right format.`;
  }
  if (element.type === "number") {
    if (element.validity.badInput || Number.isNaN(Number(value))) return `${label} must be a number.`;
    if (element.min !== "" && Number(value) < Number(element.min)) return `${label} must be ${element.min} or more.`;
  }
  return null;
}

/** The first problem in a form, as {element, message}, or null. */
export function checkForm(form) {
  for (const element of form.elements) {
    const message = fieldProblem(element);
    if (message) return { element, message };
  }
  return null;
}

/** Per-field messages for forms that show them under each input. `validate(form)` fills them and focuses the
 * first bad field; `fieldProps(id)` wires an input to its message for screen readers. */
export function useFieldErrors() {
  const [errors, setErrors] = useState({});
  const validate = (form) => {
    const found = {};
    let first = null;
    for (const element of form.elements) {
      const message = fieldProblem(element);
      const key = element.id || element.name;
      if (message && key && !found[key]) {
        found[key] = message;
        first ??= element;
      }
    }
    setErrors(found);
    first?.focus();
    return !first;
  };
  const clear = (key) => setErrors((previous) => (previous[key] ? { ...previous, [key]: undefined } : previous));
  const fieldProps = (key) => ({
    "aria-invalid": errors[key] ? true : undefined,
    "aria-describedby": errors[key] ? `${key}-error` : undefined,
  });
  return { errors, validate, clear, fieldProps };
}

export function FieldError({ id, message }) {
  if (!message) return null;
  return (
    <p className="field-error" id={`${id}-error`} role="alert">
      {message}
    </p>
  );
}
