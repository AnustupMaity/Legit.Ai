import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const statusBadgeVariants = cva(
  "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset",
  {
    variants: {
      variant: {
        safe: "bg-safe/10 text-safe ring-safe/20",
        warning: "bg-warning/10 text-warning ring-warning/20",
        danger: "bg-danger/10 text-danger ring-danger/20",
        info: "bg-info/10 text-info ring-info/20",
        monitoring: "bg-monitoring/10 text-monitoring ring-monitoring/20",
        scanning: "bg-scanning/10 text-scanning ring-scanning/20",
        protected: "bg-protected/10 text-protected ring-protected/20",
      },
      size: {
        sm: "px-2 py-0.5 text-xs",
        md: "px-3 py-1 text-xs",
        lg: "px-4 py-1.5 text-sm",
      },
    },
    defaultVariants: {
      variant: "info",
      size: "md",
    },
  }
);

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof statusBadgeVariants> {}

const StatusBadge = React.forwardRef<HTMLDivElement, StatusBadgeProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <div
        className={cn(statusBadgeVariants({ variant, size }), className)}
        ref={ref}
        {...props}
      />
    );
  }
);
StatusBadge.displayName = "StatusBadge";

export { StatusBadge, statusBadgeVariants };