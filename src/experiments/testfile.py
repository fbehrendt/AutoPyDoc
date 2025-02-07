from modulefinder import ModuleFinder

def main():
     finder = ModuleFinder()
     finder.run_script('src/experiments/create_callgraph.py')

     print('Loaded modules:')
     for name, mod in finder.modules.items():
          print('%s: ' % name, end='')
          print(','.join(list(mod.globalnames.keys())[:3]))

          print('-'*50)
          print('Modules not imported:')
          print('\n'.join(finder.badmodules.keys()))

if __name__ == "__main__":
     main()