import LabCard from "./LabCard";

function LabList() {

const labs = [

{
title: "🐍 Python Programming Lab",
description: "Ubuntu 22.04 • Python 3.12"
},

{
title: "🌐 Networking Lab",
description: "Ubuntu • Networking Tools"
},

{
title: "☁ Docker Fundamentals",
description: "Docker Engine + CLI"
}

];

  return (
    <div>
      {labs.map((lab, index) => (
        <LabCard
          key={index}
          title={lab.title}
          description={lab.description}
        />
      ))}
    </div>
  );
}

export default LabList;