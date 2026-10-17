import { Link } from "../router";

export default function Logo({ size = 36 }) {
  return (
    <Link to="/" className="logo" aria-label="QueryMind home">
      <img
        src="/QMIcon.png"
        alt=""
        width={size}
        height={size}
        className="logo-img"
      />
      <span className="logo-text">QueryMind</span>
    </Link>
  );
}