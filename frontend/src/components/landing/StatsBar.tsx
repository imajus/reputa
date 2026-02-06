const stats = [
  { value: "10,000+", label: "Addresses Analyzed" },
  { value: "$50M+", label: "Volume Tracked" },
  { value: "15+", label: "Partner Protocols" },
  { value: "<60s", label: "Migration Time" },
];

const StatsBar = () => {
  return (
    <div className="border-t border-border/40 bg-card/50 backdrop-blur-sm py-5">
      <div className="container py-6">
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-2xl font-bold text-primary md:text-3xl">
                {stat.value}
              </p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StatsBar;
