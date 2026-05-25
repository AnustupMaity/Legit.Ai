import { useNavigate } from "react-router-dom";

const Index = () => {
  const navigate = useNavigate();

  const start = () => {
    if (!localStorage.getItem("tenant_id")) {
      const uniqueId = Math.floor(Math.random() * 1000000000) + 1;
      localStorage.setItem("tenant_id", String(uniqueId));
    }
    navigate("/main");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-black text-white p-4 font-mono">
      <div className="max-w-3xl w-full border-4 border-white p-8 relative overflow-hidden">
        
        {/* Decorative corner elements */}
        <div className="absolute top-0 left-0 w-4 h-4 border-r-4 border-b-4 border-white"></div>
        <div className="absolute top-0 right-0 w-4 h-4 border-l-4 border-b-4 border-white"></div>
        <div className="absolute bottom-0 left-0 w-4 h-4 border-r-4 border-t-4 border-white"></div>
        <div className="absolute bottom-0 right-0 w-4 h-4 border-l-4 border-t-4 border-white"></div>

        <div className="text-center space-y-8">
          <div className="inline-block border-b-2 border-dashed border-white pb-4 mb-4">
            <h1 className="text-6xl md:text-8xl font-black uppercase tracking-widest">
              LEGIT.AI
            </h1>
            <p className="mt-2 text-xl md:text-2xl tracking-[0.2em] uppercase">
              System Initialization
            </p>
          </div>

          <div className="space-y-4 text-sm md:text-lg text-gray-300">
            <p className="flex justify-between border-b border-gray-700 pb-2">
              <span>&gt; DETECT.MODULE</span>
              <span>[ONLINE]</span>
            </p>
            <p className="flex justify-between border-b border-gray-700 pb-2">
              <span>&gt; ANALYSIS.CORE</span>
              <span>[ACTIVE]</span>
            </p>
            <p className="flex justify-between border-b border-gray-700 pb-2">
              <span>&gt; DEEPFAKE.SHIELD</span>
              <span>[READY]</span>
            </p>
          </div>

          <div className="pt-8">
            <button 
              onClick={start} 
              className="group relative inline-flex items-center justify-center px-8 py-4 font-bold uppercase tracking-widest text-black bg-white hover:bg-gray-200 transition-colors duration-200 focus:outline-none focus:ring-4 focus:ring-gray-500"
            >
              <span className="absolute inset-0 w-full h-full border-2 border-white group-hover:scale-105 transition-transform duration-200"></span>
              [ INITIALIZE SEQUENCE ]
            </button>
          </div>

          <div className="pt-8 mt-12 border-t-2 border-white/20 text-xs text-gray-500 uppercase tracking-widest flex flex-col items-center gap-2">
            <div className="flex justify-between w-full">
              <span>TERMINAL V1.0.4</span>
              <span>ADMIN/TRAINER SITE: DETACHED</span>
            </div>
            <span className="text-gray-400 mt-2">* Checked items are stored for 24 hours then automatically deleted *</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
