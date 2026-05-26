import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const Index = () => {
  const navigate = useNavigate();
  const [typedText, setTypedText] = useState("");

  const fullText = "AI POWERED DEEPFAKE DETECTION SYSTEM";

  useEffect(() => {
    let index = 0;

    const interval = setInterval(() => {
      setTypedText(fullText.slice(0, index));
      index++;

      if (index > fullText.length) {
        clearInterval(interval);
      }
    }, 55);

    return () => clearInterval(interval);
  }, []);

  const start = () => {
    if (!localStorage.getItem("tenant_id")) {
      const uniqueId = Math.floor(Math.random() * 1000000000) + 1;
      localStorage.setItem("tenant_id", String(uniqueId));
    }

    navigate("/main");
  };

  const modules = [
    ["DETECT.MODULE", "ONLINE"],
    ["ANALYSIS.CORE", "ACTIVE"],
    ["DEEPFAKE.SHIELD", "READY"],
    ["THREAT.INTELLIGENCE", "SCANNING"],
  ];

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-black text-white p-3 font-mono">

      {/* CINEMATIC NOISE */}
      <div 
        className="absolute inset-0 z-0 opacity-[0.04] mix-blend-overlay pointer-events-none"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }}
      ></div>

      {/* VERCEL-STYLE BRAND BADGE */}
      <div className="absolute top-6 left-6 sm:top-8 sm:left-8 flex items-center gap-3 z-50 drop-shadow-[0_0_10px_rgba(255,255,255,0.2)] hover:scale-105 transition-transform duration-300 cursor-default">
        <svg viewBox="0 0 100 100" className="w-6 h-6 sm:w-7 sm:h-7">
          <polygon points="50,20 80,75 20,75" fill="white" />
        </svg>
        <span className="font-bold text-lg sm:text-xl tracking-[0.2em] text-white">L.AI</span>
      </div>

      {/* LIVE INDICATOR */}
      <div className="absolute top-6 right-6 sm:top-8 sm:right-8 flex items-center gap-2.5 z-50 px-3 py-1.5 border border-red-500/30 bg-red-500/5 rounded-full backdrop-blur-sm">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]"></span>
        </span>
        <span className="text-[9px] sm:text-[10px] font-bold tracking-[0.25em] text-red-500/90 uppercase">SYSTEM LIVE</span>
      </div>

      {/* GRID BACKGROUND */}
      <div className="absolute inset-0 opacity-20">
        <div
          className="h-full w-full"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)
            `,
            backgroundSize: "38px 38px",
          }}
        />
      </div>

      {/* BIG GLOW */}
      <div className="absolute w-[500px] h-[500px] bg-white/5 blur-3xl rounded-full animate-pulse"></div>

      {/* SCAN LINE */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="w-full h-[2px] bg-white/10 animate-[scan_4s_linear_infinite]"></div>
      </div>

      {/* FLOATING PARTICLES */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(18)].map((_, i) => (
          <span
            key={i}
            className="absolute w-1 h-1 bg-white rounded-full opacity-20 animate-ping"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDuration: `${2 + Math.random() * 4}s`,
            }}
          />
        ))}
      </div>

      {/* MAIN CONTAINER */}
      <div className="relative z-10 w-full max-w-4xl border border-white/15 bg-black/70 backdrop-blur-md px-6 sm:px-9 py-7 overflow-hidden shadow-[0_0_45px_rgba(255,255,255,0.06)] animate-floatCard">

        {/* MOVING BORDER LIGHT */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">

          <div className="absolute top-0 left-0 w-32 h-[2px] bg-white shadow-[0_0_20px_white] animate-borderMoveX"></div>

          <div className="absolute top-0 right-0 w-[2px] h-32 bg-white shadow-[0_0_20px_white] animate-borderMoveY"></div>

          <div className="absolute bottom-0 right-0 w-32 h-[2px] bg-white shadow-[0_0_20px_white] animate-borderMoveXReverse"></div>

          <div className="absolute bottom-0 left-0 w-[2px] h-32 bg-white shadow-[0_0_20px_white] animate-borderMoveYReverse"></div>
        </div>

        {/* CORNERS */}
        <div className="absolute top-0 left-0 w-4 h-4 border-r-2 border-b-2 border-white"></div>
        <div className="absolute top-0 right-0 w-4 h-4 border-l-2 border-b-2 border-white"></div>
        <div className="absolute bottom-0 left-0 w-4 h-4 border-r-2 border-t-2 border-white"></div>
        <div className="absolute bottom-0 right-0 w-4 h-4 border-l-2 border-t-2 border-white"></div>

        <div className="text-center space-y-7">

          {/* TITLE */}
          <div className="space-y-4 animate-fadeIn">

            <h1 className="text-5xl sm:text-6xl md:text-7xl font-black uppercase tracking-[0.22em] leading-none text-white drop-shadow-[0_0_14px_rgba(255,255,255,0.4)] animate-pulse">
              LEGIT.AI
            </h1>

            <div className="h-[2px] w-36 bg-white mx-auto animate-pulse"></div>

            <p className="text-[10px] sm:text-xs md:text-sm uppercase tracking-[0.22em] text-gray-400 min-h-[18px]">
              {typedText}
              <span className="animate-pulse">_</span>
            </p>
          </div>

          {/* MODULES */}
          <div className="space-y-3 text-[10px] sm:text-xs md:text-sm text-gray-300 max-w-2xl mx-auto">

            {modules.map(([name, status], index) => (
              <div
                key={name}
                className="group relative overflow-hidden flex items-center justify-between border border-white/10 bg-white/[0.03] px-4 py-2.5 hover:bg-white/[0.09] hover:shadow-[0_0_18px_rgba(255,255,255,0.08)] transition-all duration-300 hover:scale-[1.02]"
                style={{
                  animationDelay: `${index * 150}ms`,
                }}
              >

                {/* MOVING SHINE */}
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent transition-transform duration-1000"></div>

                {/* LEFT SIDE */}
                <span className="tracking-[0.18em] truncate flex items-center gap-3">

                  {/* PULSE DOT */}
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.8)]"></span>
                  </span>

                  &gt; {name}
                </span>

                {/* STATUS */}
                <span
                  className={`flex items-center gap-2 shrink-0 ml-2 tracking-[0.15em]
                  ${status === "SCANNING"
                      ? "text-green-400 animate-pulse"
                      : "text-white"
                    }`}
                >
                  [{status}]
                </span>
              </div>
            ))}
          </div>

          {/* BUTTON */}
          <div className="pt-3">

            <button
              onClick={start}
              className="group relative inline-flex items-center justify-center overflow-hidden border border-white bg-white px-9 sm:px-11 py-3.5 text-[10px] sm:text-xs font-bold uppercase tracking-[0.3em] hover:tracking-[0.15em] text-black transition-all duration-500 hover:scale-[1.03] hover:bg-black hover:text-white hover:border-white shadow-[0_0_25px_rgba(255,255,255,0.35)] hover:shadow-[0_0_50px_rgba(255,255,255,0.7),inset_0_0_20px_rgba(255,255,255,0.4)]"
            >

              {/* BUTTON LIGHT SWEEP */}
              <span className="absolute inset-0 overflow-hidden">
                <span className="absolute top-0 left-[-120%] h-full w-[40%] bg-gradient-to-r from-transparent via-white/80 to-transparent rotate-12 group-hover:left-[140%] transition-all duration-1000"></span>
              </span>

              {/* BUTTON GLOW */}
              <span className="absolute inset-0 border border-white/30 shadow-[0_0_20px_rgba(255,255,255,0.45)] group-hover:animate-ping opacity-50"></span>

              <span className="relative z-10">
                [ INITIALIZE ]
              </span>
            </button>
          </div>

          {/* FOOTER */}
          <div className="pt-5 border-t border-white/10 text-[9px] sm:text-[10px] text-gray-500 space-y-3">

            <div className="flex justify-between uppercase tracking-[0.18em]">
              <span>TERMINAL V1.0.4</span>
              <span>STATUS : SECURE</span>
            </div>

            <p className="text-gray-400 normal-case text-center leading-relaxed">
              Checked files are automatically deleted after 24 hours.
            </p>

            {/* DEV CREDIT */}
            <div className="pt-3 border-t border-white/5 space-y-1">
              <p className="uppercase tracking-[0.3em] text-gray-600">
                Developed By
              </p>

              <h2 className="text-white text-xs sm:text-sm tracking-[0.3em] font-semibold">
                ANUSTUP MAITY
              </h2>

              <p className="text-gray-600 tracking-wide">
                © 2026 LEGIT.AI — ALL RIGHTS RESERVED
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ANIMATIONS */}
      <style>{`
        @keyframes scan {
          0% {
            transform: translateY(-100%);
          }
          100% {
            transform: translateY(100vh);
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(15px);
          }
          to {
            opacity: 1;
            transform: translateY(0px);
          }
        }

        @keyframes throb {
          0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 18px rgba(255,255,255,0.15);
          }

          50% {
            transform: scale(1.08);
            box-shadow: 0 0 35px rgba(255,255,255,0.35);
          }
        }

        @keyframes borderMoveX {
          0% {
            left: -20%;
          }
          100% {
            left: 100%;
          }
        }

        @keyframes borderMoveXReverse {
          0% {
            right: -20%;
          }
          100% {
            right: 100%;
          }
        }

        @keyframes borderMoveY {
          0% {
            top: -20%;
          }
          100% {
            top: 100%;
          }
        }

        @keyframes borderMoveYReverse {
          0% {
            bottom: -20%;
          }
          100% {
            bottom: 100%;
          }
        }

        .animate-fadeIn {
          animation: fadeIn 1s ease-out;
        }

        .animate-throb {
          animation: throb 1.8s infinite ease-in-out;
        }

        .animate-borderMoveX {
          animation: borderMoveX 4s linear infinite;
        }

        .animate-borderMoveXReverse {
          animation: borderMoveXReverse 4s linear infinite;
        }

        .animate-borderMoveY {
          animation: borderMoveY 4s linear infinite;
        }

        .animate-borderMoveYReverse {
          animation: borderMoveYReverse 4s linear infinite;
        }

        @keyframes floatCard {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-8px); }
        }

        .animate-floatCard {
          animation: floatCard 6s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
};

export default Index;