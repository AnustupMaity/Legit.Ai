import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
}

const StatCard = React.forwardRef<HTMLDivElement, StatCardProps>(
  ({ className, title, value, description, icon, trend, trendValue, ...props }, ref) => {
    return (
      <Card
        ref={ref}
        className={cn("border-2 border-white bg-black rounded-none text-white", className)}
        {...props}
      >
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 border-b-2 border-dashed border-white mb-2">
          <CardTitle className="text-sm font-bold uppercase tracking-widest">
            [{title}]
          </CardTitle>
          {icon && (
            <div className="text-white">
              {icon}
            </div>
          )}
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold tracking-widest">{value}</div>
          {(description || trendValue) && (
            <div className="flex items-center space-x-2 text-xs uppercase tracking-widest mt-2 border-t-2 border-white/20 pt-2">
              {trendValue && (
                <span className="font-bold">
                  {trend === "up" && "+"}
                  {trendValue}
                </span>
              )}
              {description && <span>{description}</span>}
            </div>
          )}
        </CardContent>
      </Card>
    );
  }
);
StatCard.displayName = "StatCard";

export { StatCard };