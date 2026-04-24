function Loader({ msg = "Loading..." }) {
  return (
    <div className="loading-wrap">
      <div className="spinner-ring" />
      <div>{msg}</div>
    </div>
  );
}

export default Loader;
