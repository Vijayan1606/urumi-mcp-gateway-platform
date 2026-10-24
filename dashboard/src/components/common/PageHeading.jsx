export function PageHeading({ eyebrow, title, subtitle, actions = null }) {
  return (
    <div className="welcome-row">
      <div className="heading-content">
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2>{title}</h2>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {actions && <div className="heading-actions">{actions}</div>}
    </div>
  );
}

export default PageHeading;
