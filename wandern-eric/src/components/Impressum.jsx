// Impressum (§ 5 DDG, § 18 Abs. 2 MStV). Address is the ladungsfähige
// c/o-Anschrift assigned by Dein Impressum (welcome mail 2026-07).
const CONTACT = {
    name: "Eric Rishmüller",
    careOf: "c/o Impressumservice Dein-Impressum",
    street: "Stettiner Str. 41",
    city: "35410 Hungen",
    country: "Deutschland",
    email: "risheric@gmail.com",
    // Number serviced by Dein Impressum; they require listing at least two
    // contact methods (email & phone).
    phone: "0157 9234 1658",
};

export default function Impressum() {
    return (
        <div className="bg-white p-6 rounded-xl shadow max-w-2xl mx-auto">
            <a href="#/" className="text-sm text-blue-400 font-semibold">
                ← Zurück zum Dashboard
            </a>

            <h2 className="mt-4 text-2xl font-bold text-blue-400">Impressum</h2>

            <h3 className="mt-6 font-semibold text-gray-900">
                Angaben gemäß § 5 DDG
            </h3>
            <p className="mt-2 text-gray-700">
                {CONTACT.name}
                <br />
                {CONTACT.careOf}
                <br />
                {CONTACT.street}
                <br />
                {CONTACT.city}
                <br />
                {CONTACT.country}
            </p>

            <h3 className="mt-6 font-semibold text-gray-900">Kontakt</h3>
            <p className="mt-2 text-gray-700">
                E-Mail: {CONTACT.email}
                <br />
                Tel.: {CONTACT.phone}
            </p>

            <h3 className="mt-6 font-semibold text-gray-900">
                Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV
            </h3>
            <p className="mt-2 text-gray-700">
                {CONTACT.name}, Anschrift wie oben.
            </p>

            <h3 className="mt-6 font-semibold text-gray-900">
                Verbraucherstreitbeilegung
            </h3>
            <p className="mt-2 text-gray-700">
                Wir sind nicht bereit oder verpflichtet, an
                Streitbeilegungsverfahren vor einer
                Verbraucherschlichtungsstelle teilzunehmen.
            </p>

            <h3 className="mt-6 font-semibold text-gray-900">
                Haftung für Links
            </h3>
            <p className="mt-2 text-gray-700">
                Diese Website enthält Links zu externen Websites Dritter, auf
                deren Inhalte kein Einfluss besteht. Für die Inhalte der
                verlinkten Seiten ist stets der jeweilige Anbieter oder
                Betreiber der Seiten verantwortlich.
            </p>
        </div>
    );
}
