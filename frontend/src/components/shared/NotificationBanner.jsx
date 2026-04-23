function NotificationBanner({ items }) {
  if (!items?.length) {
    return null;
  }

  return (
    <div className="notification-stack">
      {items.map((item) => (
        <div key={`${item.type}-${item.text}`} className={`alert alert-${item.type}`}>
          {item.text}
        </div>
      ))}
    </div>
  );
}

export default NotificationBanner;
