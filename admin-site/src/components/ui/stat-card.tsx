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
        className={cn("relative overflow-hidden", className)}
        {...props}
      >
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          {icon && (
            <div className="text-muted-foreground">
              {icon}
            </div>
          )}
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          {(description || trendValue) && (
            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
              {trendValue && (
                <span
                  className={cn(
                    "font-medium",
                    trend === "up" && "text-safe",
                    trend === "down" && "text-danger",
                    trend === "neutral" && "text-muted-foreground"
                  )}
                >
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