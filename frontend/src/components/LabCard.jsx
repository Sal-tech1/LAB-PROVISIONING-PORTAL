import { useNavigate } from "react-router-dom";

function LabCard({ title, description }) {
  const navigate = useNavigate();

  return (
    <div className="card shadow-sm border-0 mb-4">
      <div className="card-body">

        <h4 className="fw-bold">{title}</h4>

        <p className="text-muted">{description}</p>

        <button
          className="btn btn-success"
          onClick={() => navigate("/loading")}
        >
          Start Lab
        </button>

      </div>
    </div>
  );
}

export default LabCard;