'use client';

import * as Dialog from '@radix-ui/react-dialog';

export default function ConfirmDialog({ open, onOpenChange, title, description, confirmLabel = '确认', cancelLabel = '取消', onConfirm, variant = 'default' }: {
  open: boolean; onOpenChange: (o: boolean) => void; title: string; description: string;
  confirmLabel?: string; cancelLabel?: string; onConfirm: () => void; variant?: 'danger' | 'default';
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-white p-6 shadow-panel focus:outline-none">
          <Dialog.Title className="text-[14px] font-medium text-fg">{title}</Dialog.Title>
          <Dialog.Description className="mt-2 text-[13px] text-fg-secondary">{description}</Dialog.Description>
          <div className="mt-6 flex justify-end gap-2">
            <Dialog.Close asChild>
              <button className="h-8 rounded-lg border border-border bg-white px-3 text-[13px] font-medium text-fg-secondary transition-colors hover:bg-bg-hover hover:text-fg">
                {cancelLabel}
              </button>
            </Dialog.Close>
            <button onClick={() => { onConfirm(); onOpenChange(false); }}
              className={variant === 'danger'
                ? 'h-8 rounded-lg bg-red-500/10 border border-red-500/20 px-3 text-[13px] font-medium text-red-500 transition-colors hover:bg-red-500/20'
                : 'h-8 rounded-lg bg-primary px-3 text-[13px] font-medium text-white transition-colors hover:bg-primary-hover'
              }>
              {confirmLabel}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
