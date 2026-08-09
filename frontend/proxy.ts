import { NextRequest, NextResponse } from "next/server";

/**
 * Protege /admin com HTTP Basic Auth — senha única via variável de
 * ambiente (ADMIN_PASSWORD, nunca NEXT_PUBLIC_, só existe no servidor).
 * Sem ADMIN_PASSWORD configurada, o admin fica inacessível por padrão.
 *
 * As mesmas credenciais autenticam as chamadas server-to-server para o
 * backend (ver lib/admin-api.ts) — uma única senha, dois lados.
 */
export function proxy(request: NextRequest): NextResponse {
  const validPassword = process.env.ADMIN_PASSWORD;
  const validUsername = process.env.ADMIN_USERNAME ?? "admin";

  if (!validPassword) {
    return new NextResponse("Admin não configurado (ADMIN_PASSWORD ausente).", { status: 503 });
  }

  const authHeader = request.headers.get("authorization");
  if (authHeader?.startsWith("Basic ")) {
    const decoded = atob(authHeader.slice("Basic ".length));
    const separatorIndex = decoded.indexOf(":");
    const user = decoded.slice(0, separatorIndex);
    const pass = decoded.slice(separatorIndex + 1);
    if (user === validUsername && pass === validPassword) {
      return NextResponse.next();
    }
  }

  return new NextResponse("Autenticação necessária.", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="IFB Admin"' },
  });
}

export const config = {
  matcher: "/admin/:path*",
};
