import LabList from "../components/LabList";

function Dashboard() {
  return (
    <div className="container py-5">

      <div className="text-center mb-5">

        <h1 className="fw-bold text-primary">
          HydroSense Lab Portal
        </h1>

        <p className="lead">
          Welcome back, Student 👋
        </p>

        <p className="text-muted">
          Select a laboratory environment to begin your practical session.
        </p>

      </div>

      <LabList />

    </div>
  );
}

export default Dashboard;