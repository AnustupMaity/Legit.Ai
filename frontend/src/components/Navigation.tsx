import { Link, useLocation } from "react-router-dom";
import { Shield, Settings, BarChart3, AlertTriangle, Search } from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  {
    name: "Dashboard",
    href: "/main",
    icon: Shield,
  },
  {
    name: "Detect",
    href: "/detect",
    icon: Search,
  },
  {
    name: "Alerts",
    href: "/alerts",
    icon: AlertTriangle,
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function Navigation() {
  const location = useLocation();

  return (
    <nav className="flex flex-wrap justify-center sm:justify-start gap-2 p-2 border-2 border-white bg-black">
      {navigation.map((item) => {
        const isActive = location.pathname === item.href;
        return (
          <Link
            key={item.name}
            to={item.href}
            className={cn(
              "flex items-center space-x-2 px-4 py-2 text-sm font-bold uppercase tracking-widest border-2 transition-all duration-200",
              isActive
                ? "bg-white text-black border-white"
                : "text-gray-300 border-transparent hover:border-white hover:text-white"
            )}
          >
            <item.icon className="h-4 w-4" />
            <span>{item.name}</span>
          </Link>
        );
      })}
    </nav>
  );
}