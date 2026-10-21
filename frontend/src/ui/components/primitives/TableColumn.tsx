import React from "react";

export interface TableColumn<T> {
  key: string;
  header: string;
  align?: "left" | "right" | "center";
  expandable?: boolean;
  render?: (row: T) => React.ReactNode;
}
