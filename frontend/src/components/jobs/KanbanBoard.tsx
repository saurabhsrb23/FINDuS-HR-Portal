"use client";

/**
 * KanbanBoard — generic drag-and-drop column board using native HTML5 DnD.
 * Used to display pipeline stages with candidate cards in each column.
 *
 * This component is intentionally data-agnostic:
 *   columns  = array of { id, title, color }
 *   items    = array of { id, columnId, title, subtitle? }
 *   onMove   = callback invoked when a card is dropped into a new column
 */

import { useState } from "react";

export interface KanbanColumn {
  id: string;
  title: string;
  color: string;
}

export interface KanbanItem {
  id: string;
  columnId: string;
  title: string;
  subtitle?: string;
  badge?: string;
}

interface KanbanBoardProps {
  columns: KanbanColumn[];
  items: KanbanItem[];
  onMove: (itemId: string, toColumnId: string) => void;
}

export function KanbanBoard({ columns, items, onMove }: KanbanBoardProps) {
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [overColumn, setOverColumn] = useState<string | null>(null);

  function handleDragStart(itemId: string) {
    setDraggingId(itemId);
  }

  function handleDragOver(e: React.DragEvent, columnId: string) {
    e.preventDefault();
    setOverColumn(columnId);
  }

  function handleDrop(columnId: string) {
    if (draggingId) {
      const item = items.find((i) => i.id === draggingId);
      if (item && item.columnId !== columnId) {
        onMove(draggingId, columnId);
      }
    }
    setDraggingId(null);
    setOverColumn(null);
  }

  function handleDragEnd() {
    setDraggingId(null);
    setOverColumn(null);
  }

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {columns.map((col) => {
        const colItems = items.filter((i) => i.columnId === col.id);
        const isOver = overColumn === col.id;

        return (
          <div
            key={col.id}
            onDragOver={(e) => handleDragOver(e, col.id)}
            onDrop={() => handleDrop(col.id)}
            className={`flex-shrink-0 w-64 flex flex-col rounded-xl border-2 transition-colors ${
              isOver
                ? "border-indigo-400 bg-indigo-50"
                : "border-transparent bg-gray-100"
            }`}
          >
            {/* Column header */}
            <div
              className="flex items-center justify-between px-3 py-2.5 rounded-t-xl"
              style={{ backgroundColor: col.color + "22" }}
            >
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: col.color }}
                />
                <span className="text-sm font-semibold text-gray-800">
                  {col.title}
                </span>
              </div>
              <span className="text-xs bg-white rounded-full px-2 py-0.5 text-gray-600 font-medium shadow-sm">
                {colItems.length}
              </span>
            </div>

            {/* Cards */}
            <div className="flex-1 p-2 space-y-2 min-h-24">
              {colItems.map((item) => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={() => handleDragStart(item.id)}
                  onDragEnd={handleDragEnd}
                  className={`bg-white border border-gray-200 rounded-lg px-3 py-2.5 cursor-grab shadow-sm hover:shadow-md transition-all select-none ${
                    draggingId === item.id ? "opacity-40" : ""
                  }`}
                >
                  <p className="text-sm font-medium text-gray-800 line-clamp-1">
                    {item.title}
                  </p>
                  {item.subtitle && (
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">
                      {item.subtitle}
                    </p>
                  )}
                  {item.badge && (
                    <span className="inline-block mt-1.5 text-xs px-1.5 py-0.5 bg-indigo-50 text-indigo-700 rounded font-medium">
                      {item.badge}
                    </span>
                  )}
                </div>
              ))}

              {/* Drop zone hint */}
              {isOver && draggingId && (
                <div className="h-10 border-2 border-dashed border-indigo-300 rounded-lg flex items-center justify-center">
                  <span className="text-xs text-indigo-400">Drop here</span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
