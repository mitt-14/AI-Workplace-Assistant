import {
  Check,
  Circle,
  ShieldCheck,
} from "lucide-react";


function normalize(value = "") {
  return value
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}


function identityFragments(
  name = "",
  email = "",
) {
  const tokens = [];

  tokens.push(
    ...name.match(
      /[A-Za-zÀ-ÖØ-öø-ÿ0-9]+/g,
    ) || [],
  );

  const local = (
    email.split("@")[0] || ""
  );

  tokens.push(
    ...local
      .split(/[._+\-]+/)
      .filter(Boolean),
  );

  const fragments = new Set();

  for (const token of tokens) {
    const clean = normalize(token);

    if (clean.length < 3) {
      continue;
    }

    fragments.add(clean);

    if (clean.length >= 4) {
      for (
        let index = 0;
        index <= clean.length - 4;
        index += 1
      ) {
        fragments.add(
          clean.slice(
            index,
            index + 4,
          ),
        );
      }
    }
  }

  return fragments;
}


export function getPasswordChecks({
  password,
  name = "",
  email = "",
}) {
  const normalizedPassword = normalize(
    password
  );

  const fragments = identityFragments(
    name,
    email,
  );

  const noIdentity = ![
    ...fragments,
  ].some(
    (fragment) =>
      normalizedPassword.includes(
        fragment
      ),
  );

  return [
    [
      "12–128 characters",
      password.length >= 12
        && password.length <= 128,
    ],
    [
      "Uppercase letter",
      /[A-Z]/.test(password),
    ],
    [
      "Lowercase letter",
      /[a-z]/.test(password),
    ],
    [
      "Number",
      /\d/.test(password),
    ],
    [
      "Special character",
      /[^A-Za-z0-9\s]/.test(password),
    ],
    [
      "No whitespace",
      !/\s/.test(password),
    ],
    [
      "Does not contain your name or email",
      noIdentity,
    ],
  ];
}


export default function PasswordStrength(
  {
    password,
    name = "",
    email = "",
  },
) {
  const checks = getPasswordChecks({
    password,
    name,
    email,
  });

  const passed = checks.filter(
    ([, valid]) => valid
  ).length;

  const percent = Math.round(
    (passed / checks.length) * 100
  );

  return (
    <div className="mt-3 rounded-2xl border border-white/[0.07] bg-white/[0.025] p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold text-zinc-300">
          <ShieldCheck
            size={15}
            className="text-indigo-300"
          />
          Password security
        </div>
        <span className="text-[10px] text-zinc-600">
          {percent}%
        </span>
      </div>

      <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-violet-500 to-emerald-400 transition-all duration-300"
          style={{
            width: `${percent}%`,
          }}
        />
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {checks.map(
          ([label, valid]) => (
            <div
              key={label}
              className={`flex items-center gap-2 text-[11px] ${
                valid
                  ? "text-emerald-300"
                  : "text-zinc-600"
              }`}
            >
              {valid ? (
                <Check size={12} />
              ) : (
                <Circle size={9} />
              )}
              {label}
            </div>
          ),
        )}
      </div>
    </div>
  );
}
