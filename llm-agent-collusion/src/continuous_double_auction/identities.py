import random


SELLER_COMPANY_NAMES = [
    "MetalCore Industries",
    "Pinnacle Metals & Alloys",
    "GlobalMet Supply Co.",
    "Cascade Heavy Elements",
    "Titanium Valley Corporation",
    "Ferrovance Materials",
    "Summit Metallurgical Group",
    "Northern Element Trading",
    "Pacific Rim Metal Exchange",
    "Atlas Heavy Metal Solutions",
    "Benchmark Metals Corp",
    "Sterling Industrial Metals",
    "MetalWorks International",
    "Quantum Metal Resources",
    "Meridian Metallics Ltd.",
    "Imperial Element Supply",
    "Frontier Metals & Mining",
    "Horizon Heavy Metal Distributors",
    "Everest Industrial Metals",
    "Cornerstone Element Trading"
]

BUYER_COMPANY_NAMES = [
    "Apex Manufacturing",
    "Precision Components",
    "BlueRay Aerospace",
    "Nexus Electronics",
    "GreenTech Solutions",
    "Urban Infrastructure Group",
    "Quantum Defense Systems",
    "Pioneer Automotive",
    "MedTech Innovations",
    "Solaris Energy",
    "Nova Shipbuilding",
    "Atlas Construction",
    "Fusion Robotics",
    "Velocity Turbines",
    "Spectrum Devices",
    "Delta Engineering",
    "Crown Machinery",
    "Globe Power Systems",
    "Sirius Industrial Tools",
    "Vector Technologies"
]

AGENT_NAMES = [
    "Wei",
    "Nia",
    "Omar",
    "Zoe",
    "Raj",
    "Mia",
    "Leo",
    "Tara",
    "Jun",
    "Eli",
    "Yara",
    "Kit",
    "Amir",
    "Jin",
    "Maya",
    "Max",
    "Lena",
    "Theo",
    "Ana",
    "Kai"
]

# drawn from in blocks of len(base) only when a market needs them (see _pool), so smaller markets keep their names per seed
EXTRA_AGENT_NAMES = [
    "Ivo", "Noor", "Sami", "Lia", "Ravi", "Ines", "Tomas", "Aiko", "Bram", "Cleo",
    "Dev", "Esme", "Femi", "Gus", "Hana", "Ilan", "Juno", "Kofi", "Luca", "Mira",
    "Nils", "Oren", "Pia", "Quinn", "Rosa", "Seb", "Tess", "Uma", "Vik", "Wren",
]

# same rule for companies: only used above 20 sellers or 20 buyers
EXTRA_SELLER_COMPANY_NAMES = [
    "Ironbridge Alloys", "Redstone Metal Partners", "Keystone Smelting Co.", "Bluewater Metals Trading",
    "Granite Peak Materials", "Silverline Element Supply", "Oakridge Foundry Group", "Copperfield Resources",
    "Highland Ore & Metals", "Riverbend Industrial Metals",
]

EXTRA_BUYER_COMPANY_NAMES = [
    "Orion Fabrication", "Harbor Rail Systems", "Zenith Medical Devices", "Aurora Grid Solutions",
    "Cobalt Drone Works", "Meridian Packaging", "Northstar Appliances", "Ridgeway Tooling",
    "Polaris Marine Engines", "Lumen Optics",
]

def _pool(base: list[str], extra: list[str], num_names: int) -> list[str]:
    """Base pool, plus as many len(base)-sized blocks of extra names as num_names needs."""
    pool = list(base)
    for i in range(0, len(extra), len(base)):
        if num_names <= len(pool):
            break
        pool += extra[i:i + len(base)]
    return pool

def get_random_agent_names(num_names: int) -> list[str]:
    """
    Get a list of random first names.

    Args:
        num_names (int): Number of names to generate.

    Returns:
        list[str]: List of random names.
    """
    return random.sample(_pool(AGENT_NAMES, EXTRA_AGENT_NAMES, num_names), num_names)

def get_random_seller_company_names(num_names: int) -> list[str]:
    """
    Get a list of random seller company names.

    Args:
        num_names (int): Number of names to generate.

    Returns:
        list[str]: List of random seller company names.
    """
    return random.sample(_pool(SELLER_COMPANY_NAMES, EXTRA_SELLER_COMPANY_NAMES, num_names), num_names)

def get_random_buyer_company_names(num_names: int) -> list[str]:
    """
    Get a list of random buyer company names.

    Args:
        num_names (int): Number of names to generate.

    Returns:
        list[str]: List of random buyer company names.
    """
    return random.sample(_pool(BUYER_COMPANY_NAMES, EXTRA_BUYER_COMPANY_NAMES, num_names), num_names)
