'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';

const PUBLIC_ROUTES = ['/login'];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);
  const isPublic = PUBLIC_ROUTES.some((r) => pathname.startsWith(r));

  useEffect(() => {
    if (isPublic) { setChecked(true); return; }
    if (!isAuthenticated()) { router.replace('/login'); }
    else { setChecked(true); }
  }, [pathname, isPublic, router]);

  if (isPublic) return <>{children}</>;
  if (!checked) return null;
  return <>{children}</>;
}
