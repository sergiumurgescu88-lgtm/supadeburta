from ctrader_open_api.messages import OpenApiMessages_pb2 as pb

# Găsim toate clasele care conțin "Symbol" sau "Spot"
symbol_classes = [x for x in dir(pb) if 'Symbol' in x]
spot_classes = [x for x in dir(pb) if 'Spot' in x]

print("Clase disponibile pentru SIMBOLURI:")
for cls in symbol_classes:
    print(f"  - {cls}")

print("\nClase disponibile pentru PREȚURI (SPOT):")
for cls in spot_classes:
    print(f"  - {cls}")
