// Datenschutzerklärung (DSGVO). Address matches the Impressum (Dein Impressum
// c/o-Anschrift). The processing descriptions below match the actual code: no
// cookies, no analytics, one functional localStorage key, data fetched from
// GCS, and the cheer endpoint that geolocates the request IP to country only
// (specs/0006).
const CONTACT = {
    name: "Eric Rishmüller",
    careOf: "c/o Impressumservice Dein-Impressum",
    street: "Stettiner Str. 41",
    city: "35410 Hungen",
    email: "risheric@gmail.com",
};

function Section({ title, children }) {
    return (
        <>
            <h3 className="mt-6 font-semibold text-gray-900">{title}</h3>
            <div className="mt-2 text-gray-700 space-y-2">{children}</div>
        </>
    );
}

export default function Datenschutz() {
    return (
        <div className="bg-white p-6 rounded-xl shadow max-w-2xl mx-auto">
            <a href="#/" className="text-sm text-blue-400 font-semibold">
                ← Zurück zum Dashboard
            </a>

            <h2 className="mt-4 text-2xl font-bold text-blue-400">
                Datenschutzerklärung
            </h2>

            <Section title="1. Verantwortlicher">
                <p>
                    {CONTACT.name}
                    <br />
                    {CONTACT.careOf}
                    <br />
                    {CONTACT.street}
                    <br />
                    {CONTACT.city}
                    <br />
                    E-Mail: {CONTACT.email}
                </p>
            </Section>

            <Section title="2. Allgemeines">
                <p>
                    Diese Website ist ein privates Schrittzähler-Dashboard. Es
                    gibt keine Benutzerkonten, keine Cookies, kein Tracking und
                    keine Analyse-Tools. Personenbezogene Daten werden nur in
                    dem unten beschriebenen, technisch notwendigen Umfang
                    verarbeitet.
                </p>
            </Section>

            <Section title="3. Hosting (GitHub Pages)">
                <p>
                    Diese Website wird bei GitHub Pages gehostet, einem Dienst
                    der GitHub, Inc., 88 Colin P Kelly Jr St, San Francisco, CA
                    94107, USA. Beim Aufruf der Seite verarbeitet GitHub
                    technisch notwendige Daten wie die IP-Adresse in
                    Server-Logs. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO
                    (berechtigtes Interesse am zuverlässigen Betrieb der
                    Website). GitHub ist unter dem EU-US Data Privacy Framework
                    zertifiziert.
                </p>
            </Section>

            <Section title="4. Abruf der Schrittdaten (Google Cloud Storage)">
                <p>
                    Die angezeigten Schritt- und Aktivitätsdaten werden von
                    Ihrem Browser direkt aus einem öffentlichen Google Cloud
                    Storage Bucket geladen (storage.googleapis.com, Google
                    LLC). Dabei wird Ihre IP-Adresse an Google übermittelt —
                    das ist für die Auslieferung der Daten technisch
                    erforderlich. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f
                    DSGVO. Google LLC ist unter dem EU-US Data Privacy
                    Framework zertifiziert. Die Schrittdaten selbst betreffen
                    ausschließlich den Betreiber dieser Website, nicht die
                    Besucher.
                </p>
            </Section>

            <Section title='5. Support-Funktion („Cheer")'>
                <p>
                    Beim Klick auf den Support-Button wird eine Anfrage an eine
                    Google Cloud Function gesendet. Der Server leitet aus der
                    IP-Adresse der Anfrage das Herkunftsland ab; gespeichert
                    werden ausschließlich Land und Zeitstempel. Die IP-Adresse
                    selbst wird nicht gespeichert. Rechtsgrundlage ist Art. 6
                    Abs. 1 lit. f DSGVO (Missbrauchsvermeidung und anonyme
                    Statistik).
                </p>
                <p>
                    Zusätzlich merkt sich Ihr Browser lokal (localStorage,
                    Schlüssel „wandern-eric-cheered"), dass Sie in diesem Monat
                    bereits unterstützt haben. Diese Information verbleibt auf
                    Ihrem Gerät und wird nicht übertragen.
                </p>
            </Section>

            <Section title="6. Externer Link: Buy Me a Coffee">
                <p>
                    Der „Buy me a coffee"-Button ist ein einfacher Link zur
                    externen Plattform Buy Me a Coffee. Beim Anklicken
                    verlassen Sie diese Website; es gilt dann die
                    Datenschutzerklärung des dortigen Anbieters. Solange Sie
                    den Link nicht anklicken, werden keine Daten an diesen
                    Anbieter übertragen.
                </p>
            </Section>

            <Section title="7. Ihre Rechte">
                <p>
                    Sie haben nach der DSGVO das Recht auf Auskunft (Art. 15),
                    Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung
                    der Verarbeitung (Art. 18), Datenübertragbarkeit (Art. 20)
                    und Widerspruch gegen die Verarbeitung (Art. 21). Außerdem
                    haben Sie das Recht, sich bei einer
                    Datenschutz-Aufsichtsbehörde zu beschweren (Art. 77 DSGVO).
                    Wenden Sie sich dazu an die oben genannte Kontaktadresse.
                </p>
            </Section>

            <Section title="8. Verschlüsselung">
                <p>
                    Diese Website nutzt durchgehend TLS-Verschlüsselung
                    (HTTPS).
                </p>
            </Section>
        </div>
    );
}
