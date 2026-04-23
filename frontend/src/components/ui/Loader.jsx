function Loader({ msg }) {
  return (
    <div className="loading-wrap">
      <div className="spinner-ring" />
      <div className="loading-msg">{msg || "Loading..."}</div>
    </div>
  );
}

export default Loader;
