from app.analyzers.signature_analyzer import SignatureAnalyzer
def main():
    old_source="""
def process_payment(order):
    return order
"""
    new_source="""
def process_payment(order,currency):
    return order
"""
    analyzer=SignatureAnalyzer()
    old_signatures=analyzer.extract_from_source(old_source,"old.py","payment")
    new_signatures=analyzer.extract_from_source(new_source,"new.py","payment")
    changes=analyzer.compare(old_signatures,new_signatures)
    print()
    print("BlastScope")
    print("Signature Change Analysis")
    print()
    for change in changes:
        print(f"Symbol: {change.qualified_name}")
        print(f"Change: {change.change_type}")
        print(f"Breaking: {change.breaking}")
        if change.reasons:
            print("Reasons:")
            for reason in change.reasons:
                print(f"- {reason}")
if __name__=="__main__":
    main()