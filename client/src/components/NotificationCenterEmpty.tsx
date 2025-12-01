/**
 * Empty State Component for Notification Center
 */

import { Bell } from "lucide-react";
import { EmptyState } from "./EmptyState";

export function NotificationCenterEmpty() {
  return (
    <EmptyState
      icon={Bell}
      title="No notifications"
      description="You're all caught up! No new notifications at this time."
    />
  );
}

