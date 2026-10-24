import { LoadingSpinner } from "./LoadingSpinner";

export function Button({
  children,
  variant = "primary",
  size = "md",
  type = "button",
  disabled = false,
  loading = false,
  icon = null,
  onClick,
  className = "",
  style,
  ...props
}) {
  const baseClass =
    variant === "primary"
      ? "primary-button"
      : variant === "secondary"
      ? "secondary-button"
      : variant === "danger"
      ? "danger-button"
      : "text-button";

  const sizeClass = size === "sm" ? "btn-sm" : size === "lg" ? "btn-lg" : "";

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`${baseClass} ${sizeClass} ${loading ? "btn-loading" : ""} ${className}`}
      style={style}
      {...props}
    >
      {loading ? (
        <span className="btn-spinner-wrap">
          <LoadingSpinner size={14} />
          <span>{children}</span>
        </span>
      ) : (
        <span className="btn-content-wrap">
          {icon && <span className="btn-icon">{icon}</span>}
          <span>{children}</span>
        </span>
      )}
    </button>
  );
}

export default Button;
